{
  description = "Development shell for GeoGenie-backend";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python311;
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            python311
            libpq
            openssl
            zlib
            stdenv.cc.cc.lib
            pkg-config
            git
          ];

          shellHook = ''
            export VENV_DIR=".venv"
            if [ ! -d "$VENV_DIR" ]; then
              ${python.interpreter} -m venv "$VENV_DIR"
            fi
            source "$VENV_DIR/bin/activate"

            export LD_LIBRARY_PATH="${
              pkgs.lib.makeLibraryPath [
                pkgs.stdenv.cc.cc.lib
                pkgs.libpq
                pkgs.openssl
                pkgs.zlib
              ]
            }:$LD_LIBRARY_PATH"
            export PIP_DISABLE_PIP_VERSION_CHECK=1

            echo "GeoGenie dev shell ready."
            echo "Run: pip install -r requirements.txt"
          '';
        };
      }
    );
}
