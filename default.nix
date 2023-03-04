{   pyVersion ? "311"
,   isDevEnv  ? true
}:

let

commonEnv       = import ./nixpkgs {};
pkgs            = commonEnv.pkgs;

macOsDeps = with pkgs; lib.optionals stdenv.isDarwin [
    darwin.apple_sdk.frameworks.CoreServices
    darwin.apple_sdk.frameworks.ApplicationServices
];

python = pkgs."python${pyVersion}";
pythonPkgs = pkgs."python${pyVersion}Packages";

# Make a new "derivation" that represents our shell
devEnv = pkgs.mkShellNoCC {
    name = "solo";

    # The packages in the `buildInputs` list will be added to the PATH in our shell
    # Python-specific guide:
    # https://github.com/NixOS/nixpkgs/blob/master/doc/languages-frameworks/python.section.md
    buildInputs = with pkgs; [
        # see https://nixos.org/nixos/packages.html
        # Python distribution
        cookiecutter
        python
        pythonPkgs.virtualenv
        pythonPkgs.wheel
        pythonPkgs.twine
        taglib
        ncurses
        libxml2
        libxslt
        libzip
        zlib
        libressl

        libuv
        postgresql
        # root CA certificates
        cacert
        which
    ] ++ macOsDeps;
    shellHook = ''
        # set SOURCE_DATE_EPOCH so that we can use python wheels
        export SOURCE_DATE_EPOCH=$(date +%s)

        export VENV_DIR="$PWD/.venv${pyVersion}"

        export PATH=$VENV_DIR/bin:$PATH
        export PYTHONPATH=""
        export LANG=en_US.UTF-8

        export PIP_CACHE_DIR=$PWD/.local/pip-cache

        # Setup virtualenv
        if [ ! -d $VENV_DIR ]; then
            virtualenv $VENV_DIR
            $VENV_DIR/bin/python -m pip install -r requirements/minimal.txt
            $VENV_DIR/bin/python -m pip install -r requirements/local.txt
            $VENV_DIR/bin/python -m pip install -r requirements/test.txt
        fi
    '';
};

in

{
    inherit devEnv;
}
