{
  inputs = {
    nixpkgs.url = "github:StarGate01/nixpkgs/gpshell";
  };

  outputs = { self, nixpkgs }:
    let
      pkgs = nixpkgs.legacyPackages.x86_64-linux;
    in
    {
      devShell.x86_64-linux =
        pkgs.mkShell {
          shellHook = ''
          '';

          buildInputs = with pkgs; [
            globalplatform
            pkg-config
            pcsclite
            swig
            (python3.withPackages (ps: with ps; [
              setuptools
            ]))
          ];
        };
    };
}
