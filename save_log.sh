#!/bin/bash
DATE=$(date +%Y-%m-%d)
git add .cursor/ logs/ *.py *.md
git commit -m "Auto-save project snapshot [$DATE]"
git push
