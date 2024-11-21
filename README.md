
# Run NixOS inside a container with shared store

NixOS has the very cool property that it does not need anything other than
`/nix/store` to boot. With this in mind, it should be possible to build a system
derivation (creating a gc root for it), bind the store into a container and then
boot systemd inside the container.

This repository contain some scripts from experiments with starting NixOS inside
a user namespace.

- `unshare.py` is an attempt to set up the namespace with `unshare`. It is not
  very secure as it blindly binds `/sys` and `/dev`. For some reason, `agetty`
  is not able to work with the the `/dev/console` tty that we bind into the
  namespace.

- `podman.sh` is an attempt using `podman` to set up the container. This seems
  to work well. It is probably more secure, as it is reusing all the setup logic
  from `podman`.

The two approaches above bind mount the nix store read-only from the host into
the container. We can also copy all the derivations into a directory and use
that as rootfs:

```shell
for spath in $(nix-store --query --requisites result); do rsync -a $spath root/nix/store ; done
```

We can then start the container in our new root:

```shell
podman run \
       --rm \
       -it \
       --systemd=always \
       --env container=podman \
       --rootfs root:O \
       $(readlink result)/init
```

With this approach, it should be possible to run the nix daemon inside the
container.

For the case where the store is shared with the host, it might be possible to
share the socket to the nix daemon with container. The examples in this
repository do not provide daemon access inside the container.

You can build the system expression with:

```shell
nix-build container.nix
```

# Notes and resources

- https://www.freedesktop.org/wiki/Software/systemd/ContainerInterface/
- https://docs.hercules-ci.com/arion/#_minimal_plain_command_using_nixpkgs
- https://discourse.nixos.org/t/running-nix-os-containers-directly-from-the-store-with-podman/29220
- https://discourse.nixos.org/t/secure-sharing-of-nix-store-with-containers-and-vms/21087
- https://kevinboone.me/containerfromscratch_chroot.html

