set -x 

mkdir -p root

podman run \
       --rm \
       -it \
       --volume "/nix/store:/nix/store:ro" \
       --systemd=always \
       --env container=podman \
       --rootfs root:O \
       $(readlink result)/init

