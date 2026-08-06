cd /Users/kodywildfeuer/Documents/GitHub/aibast-agents-library
export FILM_SPEECH_RESOURCE_ID="/subscriptions/14d18b0c-2dd3-4e69-a8bf-641d32368046/resourceGroups/koda-ai/providers/Microsoft.CognitiveServices/accounts/koda-speech"
while pgrep -f "make.py --all --batch library" >/dev/null; do sleep 10; done
python3 -u film/kit/make.py --all --batch fy27 --engine auto
echo "FY27 BUILD DONE"
