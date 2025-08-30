    { pkgs ? import <nixpkgs> {} }:

    pkgs.mkShell {
      buildInputs = with pkgs; [
        python312 # Or your desired Python version, e.g., python310
        # Add any other system-level dependencies here
      ];

      shellHook = ''
        # Create and activate the virtual environment
        export VIRTUAL_ENV_DIR=".vert"
        if [ ! -d "$VIRTUAL_ENV_DIR" ]; then
          echo "Creating Python virtual environment..."
          python3 -m venv "$VIRTUAL_ENV_DIR"
        fi
        echo "Activating virtual environment..."
        source "$VIRTUAL_ENV_DIR"/bin/activate

        # Optional: Install Python packages with pip
        # pip install -r requirements.txt
        # Or install specific packages:
        # pip install pandas requests

        echo "Python virtual environment activated."
      '';
    }