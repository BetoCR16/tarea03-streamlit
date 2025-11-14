{
  description = "Flake with Conda environment using micromamba";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-parts.url = "github:hercules-ci/flake-parts";
  };

  outputs = { self, nixpkgs, flake-parts }:
    flake-parts.lib.mkFlake { inherit self nixpkgs; } {
      systems = [ "x86_64-linux" "aarch64-linux" ];

      perSystem = { pkgs, ... }: {
        devShells.default = pkgs.mkShell {
          packages = [
            pkgs.micromamba
          ];

          shellHook = ''
            echo "Activating Conda environment via micromamba…"
            export MAMBA_ROOT_PREFIX=$PWD/.mamba
            micromamba create -f environment.yml -y
            micromamba activate geopython-env
          '';
        };
      };
    };
}
