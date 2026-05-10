package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"github.com/spf13/cobra"

	"github.com/sentinelbr/agent/internal/config"
	"github.com/sentinelbr/agent/internal/firewall"
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
	root.AddCommand(runCmd())

	if err := root.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, "erro:", err)
		os.Exit(1)
	}
}

func versionCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "version",
		Short: "imprime a versão",
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
			log.Info("config carregado", "server", cfg.ServerEndpoint, "interval_s", cfg.HeartbeatSeconds)

			info, err := osdetect.Detect()
			if err != nil {
				return fmt.Errorf("osdetect: %w", err)
			}
			log.Info("os detectado", "family", info.Family, "distro", info.Distro)

			ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
			defer cancel()

			log.Info("agente rodando — Ctrl+C para parar")
			<-ctx.Done()
			log.Info("shutdown solicitado")
			return nil
		},
	}
}
