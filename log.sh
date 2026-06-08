#!/bin/bash
# Usage: COMMAND | bash ~/G1-Robot/log.sh
# Or:    bash ~/G1-Robot/log.sh "your text here"

REPO=~/G1-Robot
FILE=$REPO/OUTPUT.md

cd $REPO

if [ -p /dev/stdin ]; then
    # piped input
    OUTPUT=$(cat)
else
    # argument input
    OUTPUT="$1"
fi

cat > $FILE << EOF
# Terminal Output Log
## $(date '+%Y-%m-%d %H:%M:%S')

\`\`\`
$OUTPUT
\`\`\`
EOF

git add OUTPUT.md && git commit -q -m "output update" && git push -q
echo "Output pushed to GitHub."
