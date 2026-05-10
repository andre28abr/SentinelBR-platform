package config

import (
	"fmt"

	"github.com/spf13/viper"
)

type Config struct {
	ServerEndpoint   string `mapstructure:"server_endpoint"`
	HeartbeatSeconds int    `mapstructure:"heartbeat_seconds"`
	HostID           string `mapstructure:"host_id"`
	TLS              TLS    `mapstructure:"tls"`
}

type TLS struct {
	CACert     string `mapstructure:"ca_cert"`
	ClientCert string `mapstructure:"client_cert"`
	ClientKey  string `mapstructure:"client_key"`
}

// Load procura o config em (em ordem):
//   1. caminho explícito passado por --config
//   2. ./agent.yaml
//   3. /etc/sentinelbr/agent.yaml
//
// Variáveis de ambiente prefixadas com SENTINEL_ sobrescrevem
// (ex: SENTINEL_SERVER_ENDPOINT=https://...).
func Load(explicit string) (*Config, error) {
	v := viper.New()
	v.SetConfigType("yaml")

	v.SetDefault("server_endpoint", "localhost:9443")
	v.SetDefault("heartbeat_seconds", 30)

	v.SetEnvPrefix("SENTINEL")
	v.AutomaticEnv()

	if explicit != "" {
		v.SetConfigFile(explicit)
	} else {
		v.SetConfigName("agent")
		v.AddConfigPath(".")
		v.AddConfigPath("/etc/sentinelbr")
	}

	if err := v.ReadInConfig(); err != nil {
		// arquivo opcional — se não achar, usa defaults + env
		if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
			return nil, fmt.Errorf("ler config: %w", err)
		}
	}

	var cfg Config
	if err := v.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("unmarshal config: %w", err)
	}
	return &cfg, nil
}
