# Theme carrier image: holds the theme files and copies them into a shared
# volume at /target on start, then exits. Use it as a sidecar (compose) or an
# init container (Kubernetes) next to the official Keycloak image — no Keycloak
# rebuild needed.
FROM busybox:1.37

LABEL org.opencontainers.image.source="https://github.com/nd4y/keycloak-theme-material3" \
      org.opencontainers.image.description="Material 3 Expressive theme for Keycloak (theme files carrier image)" \
      org.opencontainers.image.licenses="MIT"

COPY theme/material3 /theme/material3

# Wipe the target first so file deletions in the theme propagate on upgrades.
CMD ["/bin/sh", "-c", "rm -rf /target/* && cp -a /theme/material3/. /target/ && echo 'Material 3 theme copied to /target'"]
