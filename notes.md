Deps:

```
pip install requests openai python-fasthtml dotenv
```

---

8/16/25:
For running on NixOS:

We created shell.nix file and added stuff to it to make the python venv work.

So when we need to run our virtual environment, we need to use the nix shell:

nix-shell

When the nix shell starts up, the shell.nix file describes what will happen. It will activate our python virtual environment for us (.vert)

From there, you can do all the normal python/pip stuff.

8/20/2025:

On Nix OS, most if not all system libraries are symbolically linked. To avoid having problems with the venv folder, we use the following flag:

```
python -m venv .venv --copies
```

VSCode will then fully recognize this folder and auto-activate it.
