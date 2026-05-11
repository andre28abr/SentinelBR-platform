// Package grpcclient encapsula o cliente gRPC do agente, configurado com mTLS
// usando o cert assinado pela CA do servidor durante o enrollment.
package grpcclient

import (
	"crypto/tls"
	"crypto/x509"
	"errors"
	"fmt"
	"os"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"

	pb "github.com/sentinelbr/agent/internal/grpc/pb"
)

// ServerName usado na verificacao do cert do server. Deve casar com SAN no cert do servidor.
const ServerName = "sentinelbr-server"

func Dial(endpoint, caPath, certPath, keyPath string) (*grpc.ClientConn, pb.AgentServiceClient, error) {
	cert, err := tls.LoadX509KeyPair(certPath, keyPath)
	if err != nil {
		return nil, nil, fmt.Errorf("carregar cert/key do client: %w", err)
	}

	caBytes, err := os.ReadFile(caPath)
	if err != nil {
		return nil, nil, fmt.Errorf("ler CA: %w", err)
	}
	pool := x509.NewCertPool()
	if !pool.AppendCertsFromPEM(caBytes) {
		return nil, nil, errors.New("CA PEM invalido")
	}

	tlsConfig := &tls.Config{
		Certificates: []tls.Certificate{cert},
		RootCAs:      pool,
		ServerName:   ServerName,
		MinVersion:   tls.VersionTLS13,
	}

	conn, err := grpc.NewClient(endpoint, grpc.WithTransportCredentials(credentials.NewTLS(tlsConfig)))
	if err != nil {
		return nil, nil, fmt.Errorf("dial gRPC %s: %w", endpoint, err)
	}
	return conn, pb.NewAgentServiceClient(conn), nil
}
