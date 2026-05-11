package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/spf13/cobra"

	"github.com/sentinelbr/agent/internal/agentstate"
	"github.com/sentinelbr/agent/internal/config"
	"github.com/sentinelbr/agent/internal/enrollclient"
	"github.com/sentinelbr/agent/internal/firewall"
	"github.com/sentinelbr/agent/internal/grpcclient"
	"github.com/sentinelbr/agent/internal/heartbeat"
	"github.com/sentinelbr/agent/internal/logging"
	"github.com/sentinelbr/agent/internal/mac"
	"github.com/sentinelbr/agent/internal/osdetect"
	"github.com/sentinelbr/agent/internal/packagemgr"
)

var version = "dev"

func main() {
	root := &cobra.Command{
		Use:           "sentinel-agent",
		Short:         "SentinelBR — coletor de host (Linux/Windows/macOS-dev)",
		SilenceUsage:  true,
		SilenceErrors: true,
	}

	root.PersistentFlags().String("config", "", "caminho para config (default: /etc/sentinelbr/agent.yaml)")
	root.PersistentFlags().String("log-level", "info", "debug|info|warn|error")

	root.AddCommand(versionCmd())
	root.AddCommand(doctorCmd())
	root.AddCommand(enrollCmd())
	root.AddCommand(runCmd())

	if err := root.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, "erro:", err)
		os.Exit(1)
	}
}

func versionCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "version",
		Short: "imprime a versao",
		Run: func(_ *cobra.Command, _ []string) {
			fmt.Printf("sentinel-agent %s\n", version)
		},
	}
}

func doctorCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "doctor",
		Short: "detecta o ambiente e lista capabilities",
		RunE: func(cmd *cobra.Command, _ []string) error {
			level, _ := cmd.Flags().GetString("log-level")
			log := logging.New(level)

			info, err := osdetect.Detect()
			if err != nil {
				return fmt.Errorf("falha ao detectar OS: %w", err)
			}

			fmt.Printf("OS detectado:\n")
			fmt.Printf("  family       = %s\n", info.Family)
			fmt.Printf("  distro       = %s\n", info.Distro)
			fmt.Printf("  version      = %s\n", info.Version)
			fmt.Printf("  arch         = %s\n", info.Arch)
			fmt.Printf("  kernel       = %s\n", info.Kernel)
			fmt.Printf("  package_mgr  = %s\n", info.PackageMgr)
			fmt.Printf("  init_system  = %s\n", info.InitSystem)
			fmt.Printf("  firewall     = %s\n", info.FirewallTool)
			fmt.Printf("  mac_system   = %s\n", info.MACSystem)

			pm := packagemgr.New(info)
			fw := firewall.New(info)
			mc := mac.New(info)

			fmt.Printf("\nCapabilities:\n")
			fmt.Printf("  package mgr  = %s (impl: %T)\n", pm.Name(), pm)
			fmt.Printf("  firewall     = %s (impl: %T)\n", fw.Backend(), fw)
			fmt.Printf("  mac          = %s (impl: %T)\n", mc.Name(), mc)

			log.Info("doctor finished", "os", info.Distro, "version", info.Version)
			return nil
		},
	}
}

func enrollCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "enroll",
		Short: "registra esse host no servidor (one-shot, requer token gerado no UI)",
		RunE: func(cmd *cobra.Command, _ []string) error {
			level, _ := cmd.Flags().GetString("log-level")
			log := logging.New(level)

			server, _ := cmd.Flags().GetString("server")
			grpcEndpoint, _ := cmd.Flags().GetString("grpc")
			token, _ := cmd.Flags().GetString("token")

			if server == "" || token == "" {
				return fmt.Errorf("--server e --token sao obrigatorios")
			}
			if grpcEndpoint == "" {
				grpcEndpoint = "localhost:9443"
			}

			info, err := osdetect.Detect()
			if err != nil {
				return fmt.Errorf("osdetect: %w", err)
			}
			hostname, _ := os.Hostname()

			log.Info("enrolling", "server", server, "hostname", hostname, "distro", info.Distro)
			resp, err := enrollclient.Enroll(server, token, hostname, info)
			if err != nil {
				return err
			}

			dir, err := agentstate.DefaultDir()
			if err != nil {
				return err
			}
			st := agentstate.State{
				HostID:       resp.HostID,
				GRPCEndpoint: orDefault(resp.GRPCEndpoint, grpcEndpoint),
				ServerURL:    server,
			}
			if err := agentstate.Save(dir, st, []byte(resp.CACertPEM), []byte(resp.ClientCertPEM), []byte(resp.ClientKeyPEM)); err != nil {
				return err
			}

			fmt.Printf("✓ enrolled como %s\n", resp.HostID)
			fmt.Printf("  certs salvos em: %s\n", dir)
			fmt.Printf("  rode: sentinel-agent run\n")
			return nil
		},
	}
	cmd.Flags().String("server", "", "URL do server REST (ex: http://localhost:8000)")
	cmd.Flags().String("grpc", "", "endpoint gRPC (default: vem da resposta do enrollment)")
	cmd.Flags().String("token", "", "enrollment token gerado no UI")
	return cmd
}

func runCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "run",
		Short: "roda o loop do agente (heartbeat + coletores)",
		RunE: func(cmd *cobra.Command, _ []string) error {
			cfgPath, _ := cmd.Flags().GetString("config")
			level, _ := cmd.Flags().GetString("log-level")

			log := logging.New(level)

			cfg, err := config.Load(cfgPath)
			if err != nil {
				return fmt.Errorf("config: %w", err)
			}

			dir, err := agentstate.DefaultDir()
			if err != nil {
				return err
			}
			st, paths, err := agentstate.Load(dir)
			if err != nil {
				return err
			}
			log.Info("state carregado", "host_id", st.HostID, "grpc", st.GRPCEndpoint)

			conn, client, err := grpcclient.Dial(st.GRPCEndpoint, paths.CACert, paths.ClientCert, paths.ClientKey)
			if err != nil {
				return fmt.Errorf("dial gRPC: %w", err)
			}
			defer conn.Close()

			ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
			defer cancel()

			interval := time.Duration(cfg.HeartbeatSeconds) * time.Second
			loop := &heartbeat.Loop{
				Client:   client,
				HostID:   st.HostID,
				Interval: interval,
				Log:      log,
			}

			log.Info("agente rodando — Ctrl+C para parar", "interval", interval.String())
			return loop.Run(ctx)
		},
	}
}

func orDefault(v, d string) string {
	if v == "" {
		return d
	}
	return v
}
