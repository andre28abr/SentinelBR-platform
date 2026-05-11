package main

import (
	"context"
	"errors"
	"fmt"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/spf13/cobra"
	"golang.org/x/sync/errgroup"
	"google.golang.org/protobuf/types/known/timestamppb"

	"github.com/sentinelbr/agent/internal/agentstate"
	"github.com/sentinelbr/agent/internal/cmddispatcher"
	"github.com/sentinelbr/agent/internal/collectors"
	"github.com/sentinelbr/agent/internal/config"
	"github.com/sentinelbr/agent/internal/enrollclient"
	"github.com/sentinelbr/agent/internal/eventstream"
	"github.com/sentinelbr/agent/internal/events"
	"github.com/sentinelbr/agent/internal/filewatcher"
	"github.com/sentinelbr/agent/internal/firewall"
	pb "github.com/sentinelbr/agent/internal/grpc/pb"
	"github.com/sentinelbr/agent/internal/grpcclient"
	"github.com/sentinelbr/agent/internal/heartbeat"
	"github.com/sentinelbr/agent/internal/logging"
	"github.com/sentinelbr/agent/internal/mac"
	"github.com/sentinelbr/agent/internal/osdetect"
	"github.com/sentinelbr/agent/internal/packagemgr"
	"github.com/sentinelbr/agent/internal/quarantine"
	"github.com/sentinelbr/agent/internal/yarascanner"
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
	root.AddCommand(inventoryCmd())
	root.AddCommand(scanCmd())

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
	cmd := &cobra.Command{
		Use:   "run",
		Short: "roda o loop do agente (heartbeat + coletores)",
		RunE: func(cmd *cobra.Command, _ []string) error {
			cfgPath, _ := cmd.Flags().GetString("config")
			level, _ := cmd.Flags().GetString("log-level")
			sshSourceFile, _ := cmd.Flags().GetString("ssh-source-file")
			sshSourceOnce, _ := cmd.Flags().GetBool("ssh-source-once")
			macSourceFile, _ := cmd.Flags().GetString("mac-source-file")
			macSourceOnce, _ := cmd.Flags().GetBool("mac-source-once")
			firewallDryRun, _ := cmd.Flags().GetBool("firewall-dry-run")
			yaraRulesPath, _ := cmd.Flags().GetString("yara-rules-path")
			yaraWatchDirs, _ := cmd.Flags().GetStringSlice("yara-watch-dir")
			quarantineDir, _ := cmd.Flags().GetString("quarantine-dir")
			quarantineDryRun, _ := cmd.Flags().GetBool("quarantine-dry-run")

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
			info, _ := osdetect.Detect()
			fw := firewall.New(info)

			// fan-in: todos os collectors emitem em `eventBus` que vira o input do stream.
			eventBus := make(chan *events.Event, 256)
			var wg sync.WaitGroup

			var quar *quarantine.Quarantiner
			if !quarantineDryRun {
				quar = quarantine.New(quarantineDir)
			}

			dispatcher := &cmddispatcher.Dispatcher{
				Firewall:      fw,
				DryRun:        firewallDryRun,
				Log:           log,
				HostID:        st.HostID,
				YaraRulesPath: yaraRulesPath,
				EventBus:      eventBus,
				Quarantiner:   quar,
			}
			if firewallDryRun {
				log.Info("firewall em modo DRY-RUN — nada sera executado de verdade")
			} else {
				log.Info("firewall configurado", "backend", fw.Backend())
			}
			if yaraRulesPath != "" {
				log.Info("yara habilitado", "rules", yaraRulesPath)
			}
			if quarantineDryRun {
				log.Info("quarantine em modo DRY-RUN — nada sera movido")
			}

			hbLoop := &heartbeat.Loop{
				Client:     client,
				Dispatcher: dispatcher,
				HostID:     st.HostID,
				Interval:   interval,
				Log:        log,
			}

			sshSource := pickSSHSource(sshSourceFile, sshSourceOnce)
			if sshSource != nil {
				col := collectors.NewSSHDCollector(st.HostID, sshSource)
				wg.Add(1)
				go func() {
					defer wg.Done()
					if err := col.Run(ctx); err != nil {
						log.Error("collector sshd parou", "err", err)
					}
				}()
				wg.Add(1)
				go func() {
					defer wg.Done()
					for ev := range col.Events() {
						select {
						case <-ctx.Done():
							return
						case eventBus <- ev:
						}
					}
				}()
				log.Info("collector sshd ativo", "source", sshSource.Name())
			} else {
				log.Info("nenhum collector sshd configurado (use --ssh-source-file pra dev)")
			}

			// MAC collector (SELinux ou AppArmor) baseado no MAC system detectado.
			macSource := pickMACSource(macSourceFile, macSourceOnce)
			if macSource != nil {
				kind := pickMACKind(info)
				if kind == "" {
					log.Warn("MAC source configurado mas OS sem SELinux/AppArmor — descartando")
				} else {
					col := collectors.NewMACCollector(kind, st.HostID, macSource)
					wg.Add(1)
					go func() {
						defer wg.Done()
						if err := col.Run(ctx); err != nil {
							log.Error("collector mac parou", "err", err, "kind", string(kind))
						}
					}()
					wg.Add(1)
					go func() {
						defer wg.Done()
						for ev := range col.Events() {
							select {
							case <-ctx.Done():
								return
							case eventBus <- ev:
							}
						}
					}()
					log.Info("collector mac ativo", "kind", string(kind), "source", macSource.Name())
				}
			}

			// File watcher (YARA on-write). So liga se -yara-watch-dir e -yara-rules-path setados.
			if len(yaraWatchDirs) > 0 && yaraRulesPath != "" {
				fw := &filewatcher.Watcher{
					HostID:         st.HostID,
					Dirs:           yaraWatchDirs,
					RulesPath:      yaraRulesPath,
					EventBus:       eventBus,
					Log:            log,
					IgnoreSuffixes: []string{".swp", ".tmp", "~"},
				}
				wg.Add(1)
				go func() {
					defer wg.Done()
					if err := fw.Run(ctx); err != nil {
						log.Error("filewatcher parou", "err", err)
					}
				}()
				log.Info("filewatcher YARA ativo", "dirs", yaraWatchDirs)
			} else if len(yaraWatchDirs) > 0 && yaraRulesPath == "" {
				log.Warn("--yara-watch-dir ignorado: --yara-rules-path obrigatorio")
			}

			// Quando todos os collectors fecharem, fecha o eventBus pra terminar o stream.
			go func() {
				wg.Wait()
				close(eventBus)
			}()

			sender := &eventstream.Sender{Client: client, Log: log}
			g, gctx := errgroup.WithContext(ctx)
			g.Go(func() error { return hbLoop.Run(gctx) })
			g.Go(func() error { return sender.Run(gctx, eventBus) })

			log.Info("agente rodando — Ctrl+C para parar", "interval", interval.String())
			if err := g.Wait(); err != nil && !errors.Is(err, context.Canceled) {
				return err
			}
			return nil
		},
	}
	cmd.Flags().String("ssh-source-file", "", "le eventos sshd desse arquivo (vazio = desabilitado). Em prod: /var/log/auth.log")
	cmd.Flags().Bool("ssh-source-once", false, "le o arquivo do --ssh-source-file ate EOF e sai (modo replay). Default: tail -F")
	cmd.Flags().String("mac-source-file", "", "le eventos SELinux/AppArmor desse arquivo. Em prod: /var/log/audit/audit.log (selinux) ou /var/log/syslog (apparmor)")
	cmd.Flags().Bool("mac-source-once", false, "modo replay pro --mac-source-file. Default: tail -F")
	cmd.Flags().Bool("firewall-dry-run", false, "loga BlockIP/UnblockIP em vez de executar (uso em dev, ou Mac sem nft/firewall-cmd)")
	cmd.Flags().String("yara-rules-path", "", "diretorio ou arquivo .yar (habilita run_yara_scan e filewatcher)")
	cmd.Flags().StringSlice("yara-watch-dir", nil, "diretorio a monitorar para scan YARA on-write (repetivel; requer --yara-rules-path)")
	cmd.Flags().String("quarantine-dir", "", "destino dos arquivos em quarentena (default: /var/sentinelbr/quarantine)")
	cmd.Flags().Bool("quarantine-dry-run", false, "loga quarantine em vez de mover arquivos (uso em dev)")
	return cmd
}

func pickSSHSource(fileFlag string, once bool) collectors.Source {
	if fileFlag != "" {
		return collectors.NewFileSource(fileFlag, once)
	}
	return nil
}

func inventoryCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "inventory",
		Short: "envia lista de pacotes instalados pro server (cross-ref com OSV)",
		RunE: func(cmd *cobra.Command, _ []string) error {
			level, _ := cmd.Flags().GetString("log-level")
			log := logging.New(level)

			info, err := osdetect.Detect()
			if err != nil {
				return fmt.Errorf("osdetect: %w", err)
			}

			pm := packagemgr.New(info)
			log.Info("listando pacotes", "package_mgr", pm.Name())
			pkgs, err := pm.ListInstalled()
			if err != nil {
				return fmt.Errorf("listar pacotes (%s): %w", pm.Name(), err)
			}
			if len(pkgs) == 0 {
				return fmt.Errorf("nenhum pacote retornado — package mgr suportado nesse OS?")
			}

			dir, err := agentstate.DefaultDir()
			if err != nil {
				return err
			}
			st, paths, err := agentstate.Load(dir)
			if err != nil {
				return err
			}

			conn, client, err := grpcclient.Dial(st.GRPCEndpoint, paths.CACert, paths.ClientCert, paths.ClientKey)
			if err != nil {
				return fmt.Errorf("dial gRPC: %w", err)
			}
			defer conn.Close()

			pbPackages := make([]*pb.PackageInfo, 0, len(pkgs))
			for _, p := range pkgs {
				pbPackages = append(pbPackages, &pb.PackageInfo{
					Name: p.Name, Version: p.Version, Arch: p.Arch,
				})
			}

			ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
			defer cancel()

			resp, err := client.SubmitInventory(ctx, &pb.InventoryReport{
				HostId:      st.HostID,
				Source:      pkgs[0].Source,
				CollectedAt: timestamppb.Now(),
				Packages:    pbPackages,
			})
			if err != nil {
				return fmt.Errorf("SubmitInventory RPC: %w", err)
			}

			fmt.Printf("✓ inventory enviado: %d pacotes (scan agendado: %v)\n",
				resp.PackagesReceived, resp.ScanScheduled)
			return nil
		},
	}
}

func pickMACSource(fileFlag string, once bool) collectors.Source {
	if fileFlag != "" {
		return collectors.NewFileSource(fileFlag, once)
	}
	return nil
}

func pickMACKind(info *osdetect.OSInfo) collectors.MACKind {
	if info == nil {
		return ""
	}
	switch info.MACSystem {
	case "selinux":
		return collectors.MACKindSELinux
	case "apparmor":
		return collectors.MACKindAppArmor
	}
	// Em Mac dev (info.MACSystem="none"), assume SELinux pra fixture testing
	// — o usuario pode passar uma fixture de qualquer formato e o parser certo
	// vai casar/silenciar conforme o conteudo.
	return collectors.MACKindSELinux
}

func orDefault(v, d string) string {
	if v == "" {
		return d
	}
	return v
}

func scanCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "scan",
		Short: "roda YARA contra um diretorio e envia matches como eventos",
		RunE: func(cmd *cobra.Command, _ []string) error {
			level, _ := cmd.Flags().GetString("log-level")
			path, _ := cmd.Flags().GetString("path")
			rulesPath, _ := cmd.Flags().GetString("rules-path")
			sendEvents, _ := cmd.Flags().GetBool("send-events")

			log := logging.New(level)

			if path == "" {
				return fmt.Errorf("--path obrigatorio (ex: /var/www, /tmp/x)")
			}
			if rulesPath == "" {
				rulesPath = "yara-rules"  // default: relativo ao cwd, util pro Mac dev
			}

			scanner, err := yarascanner.NewScanner("placeholder-host-id", rulesPath)
			if err != nil {
				return err
			}

			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
			defer cancel()

			log.Info("rodando yara", "path", path, "rules", rulesPath)
			matches, err := scanner.Scan(ctx, path)
			if err != nil {
				return err
			}

			fmt.Printf("✓ scan completo: %d matches\n", len(matches))
			for _, m := range matches {
				fmt.Printf("  [%s] %s -> %s\n", m.Severity, m.RuleName, m.FilePath)
			}

			if !sendEvents || len(matches) == 0 {
				return nil
			}

			// Envia matches via gRPC. Carrega state pra pegar host_id real.
			dir, err := agentstate.DefaultDir()
			if err != nil {
				return err
			}
			st, paths, err := agentstate.Load(dir)
			if err != nil {
				log.Warn("agente nao enrollado, pulando envio de eventos", "err", err)
				return nil
			}

			scanner.HostID = st.HostID
			evs, err := scanner.ScanToEvents(ctx, path)
			if err != nil {
				return err
			}

			conn, client, err := grpcclient.Dial(st.GRPCEndpoint, paths.CACert, paths.ClientCert, paths.ClientKey)
			if err != nil {
				return fmt.Errorf("dial gRPC: %w", err)
			}
			defer conn.Close()

			sender := &eventstream.Sender{Client: client, Log: log}
			eventBus := make(chan *events.Event, len(evs))
			for _, ev := range evs {
				eventBus <- ev
			}
			close(eventBus)

			if err := sender.Run(ctx, eventBus); err != nil {
				return fmt.Errorf("stream: %w", err)
			}
			fmt.Printf("✓ %d eventos enviados ao server\n", len(evs))
			return nil
		},
	}
	cmd.Flags().String("path", "", "diretorio (ou arquivo) a escanear")
	cmd.Flags().String("rules-path", "", "diretorio ou arquivo .yar (default: ./yara-rules)")
	cmd.Flags().Bool("send-events", true, "envia matches via gRPC pro server (precisa enroll previo)")
	return cmd
}
