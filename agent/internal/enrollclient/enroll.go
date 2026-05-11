// Package enrollclient faz o POST /api/v1/agents/enroll para trocar token por certs.
package enrollclient

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/sentinelbr/agent/internal/osdetect"
)

type osPayload struct {
	Family         string `json:"family"`
	Distro         string `json:"distro"`
	Version        string `json:"version,omitempty"`
	Arch           string `json:"arch,omitempty"`
	Kernel         string `json:"kernel,omitempty"`
	PackageManager string `json:"package_manager,omitempty"`
	InitSystem     string `json:"init_system,omitempty"`
	FirewallTool   string `json:"firewall_tool,omitempty"`
	MACSystem      string `json:"mac_system,omitempty"`
}

type request struct {
	Token    string    `json:"token"`
	Hostname string    `json:"hostname"`
	OS       osPayload `json:"os"`
}

type Response struct {
	HostID       string `json:"host_id"`
	CACertPEM    string `json:"ca_cert_pem"`
	ClientCertPEM string `json:"client_cert_pem"`
	ClientKeyPEM  string `json:"client_key_pem"`
	GRPCEndpoint string `json:"grpc_endpoint"`
}

type apiError struct {
	Detail any `json:"detail"`
}

func Enroll(serverURL, token, hostname string, info *osdetect.OSInfo) (*Response, error) {
	body := request{
		Token:    token,
		Hostname: hostname,
		OS: osPayload{
			Family:         info.Family,
			Distro:         info.Distro,
			Version:        info.Version,
			Arch:           info.Arch,
			Kernel:         info.Kernel,
			PackageManager: info.PackageMgr,
			InitSystem:     info.InitSystem,
			FirewallTool:   info.FirewallTool,
			MACSystem:      info.MACSystem,
		},
	}
	payload, err := json.Marshal(body)
	if err != nil {
		return nil, fmt.Errorf("marshal: %w", err)
	}

	url := serverURL + "/api/v1/agents/enroll"
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(payload))
	if err != nil {
		return nil, fmt.Errorf("build request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("POST %s: %w", url, err)
	}
	defer resp.Body.Close()

	respBody, _ := io.ReadAll(resp.Body)

	if resp.StatusCode >= 400 {
		var apiErr apiError
		if json.Unmarshal(respBody, &apiErr) == nil {
			return nil, fmt.Errorf("enrollment falhou (HTTP %d): %v", resp.StatusCode, apiErr.Detail)
		}
		return nil, fmt.Errorf("enrollment falhou (HTTP %d): %s", resp.StatusCode, string(respBody))
	}

	var out Response
	if err := json.Unmarshal(respBody, &out); err != nil {
		return nil, fmt.Errorf("parse response: %w", err)
	}
	return &out, nil
}
