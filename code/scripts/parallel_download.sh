#!/usr/bin/env bash
# Parallel chunked download of model.safetensors into part files, then install
# into the HF cache. Re-runnable: completed parts are skipped, signed URL is
# refreshed each run. Verify at the end: sha256 == x-linked-etag of the file.
set -u
cd "$(dirname "$0")/.."

REPO_URL="https://huggingface.co/bodhan-ai/indic-transcribe-core/resolve/4d29eeb7a0990de4a8febf9a4d5a9c5c61134a0d/model.safetensors"
TOTAL=4890451120
SHA=fcc2284a6e0154989743dc20b0232e4e285b770429f306029f01a661b9c6200c
PARTS_DIR="data/model_download_parts"
NCHUNK=48
CHUNK=$(( (TOTAL + NCHUNK - 1) / NCHUNK ))
TOKEN=$(grep HF_TOKEN .env | cut -d= -f2)
PAR=16

mkdir -p "$PARTS_DIR"
refresh_url() {
  curl -sI --max-time 30 -H "Authorization: Bearer $TOKEN" "$REPO_URL" \
    | grep -i '^location:' | tr -d '\r' | awk '{print $2}'
}

URL=$(refresh_url)
[ -z "$URL" ] && { echo "FATAL: could not obtain signed URL (network? token?)"; exit 1; }
echo "signed URL OK, ${NCHUNK} chunks x ~${CHUNK} bytes, parallel=${PAR}"

for ((c=0; c<NCHUNK; c++)); do
  (
    part=$(printf '%s/part_%03d' "$PARTS_DIR" "$c")
    start=$(( c * CHUNK ))
    end=$(( start + CHUNK - 1 ))
    [ $end -ge $TOTAL ] && end=$(( TOTAL - 1 ))
    want=$(( end - start + 1 ))
    have=0; [ -f "$part" ] && have=$(stat -f%z "$part")
    [ "$have" -eq "$want" ] && exit 0
    u=$(refresh_url); [ -z "$u" ] && u="$URL"
    for attempt in 1 2 3 4 5; do
      have=0; [ -f "$part" ] && have=$(stat -f%z "$part")
      [ "$have" -ge "$want" ] && exit 0
      from=$(( start + have ))
      curl -sL --max-time 480 --speed-limit 10240 --speed-time 30 \
        -H "Authorization: Bearer $TOKEN" -r "${from}-${end}" "$u" >> "$part" && exit 0
      sleep $(( attempt * 3 ))
      u=$(refresh_url); [ -z "$u" ] && u="$URL"
    done
    echo "CHUNK $c FAILED after retries"
  ) &
  while [ "$(jobs -rp | wc -l | tr -d ' ')" -ge "$PAR" ]; do sleep 1; done
done
wait
if ls "$PARTS_DIR"/part_* 2>/dev/null | wc -l | grep -qv .; then :; fi
incomplete=0
for ((c=0; c<NCHUNK; c++)); do
  part=$(printf '%s/part_%03d' "$PARTS_DIR" "$c")
  start=$(( c * CHUNK )); end=$(( start + CHUNK - 1 )); [ $end -ge $TOTAL ] && end=$(( TOTAL - 1 ))
  want=$(( end - start + 1 )); have=0; [ -f "$part" ] && have=$(stat -f%z "$part")
  [ "$have" -eq "$want" ] || { echo "INCOMPLETE chunk $c: $have/$want"; incomplete=1; }
done
[ $incomplete -eq 1 ] && { echo "NOT READY — re-run to resume"; exit 2; }

echo "--- all chunks present, hashing ---"
HASH=$(for ((c=0; c<NCHUNK; c++)); do
  cat "$(printf '%s/part_%03d' "$PARTS_DIR" "$c")" || exit 1
done | shasum -a 256 | awk '{print $1}')
echo "sha256=$HASH"
if [ "$HASH" != "$SHA" ]; then echo "SHA MISMATCH — do not use"; exit 3; fi
echo "SHA OK — assembling"
for ((c=0; c<NCHUNK; c++)); do
  cat "$(printf '%s/part_%03d' "$PARTS_DIR" "$c")" || exit 1
done > data/model.safetensors
echo "ASSEMBLED data/model.safetensors"
