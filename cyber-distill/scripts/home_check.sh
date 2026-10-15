# Report files a setup step wrote under $HOME, which is small on Marlowe (32 GB). Source, then:
#   home_mark            # before the step
#   home_check           # after it: lists new files under ~ and returns 1 if there are any
# Shell history and editor state (code-server) are ignored.
home_mark() { HOME_MARK=$(mktemp "${SCRATCH_BASE:-${TMPDIR:-/tmp}}/.home_mark.XXXXXX"); }
home_check() {
  local new
  new=$(find "$HOME" -newer "$HOME_MARK" -type f ! -name '.bash_history' ! -path '*/code-server/*' 2>/dev/null)
  rm -f "$HOME_MARK"
  if [ -n "$new" ]; then
    echo "WARNING: files written under $HOME (move them to scratch and fix the variable that sent them there):"
    echo "$new"
    return 1
  fi
  echo "home check: nothing written under $HOME"
}
