cd /Users/kodywildfeuer/Documents/GitHub/aibast-agents-library
export FILM_SPEECH_RESOURCE_ID="/subscriptions/14d18b0c-2dd3-4e69-a8bf-641d32368046/resourceGroups/koda-ai/providers/Microsoft.CognitiveServices/accounts/koda-speech"
python3 -u film/kit/make.py --all --batch fy27 --engine auto --skip narrate
python3 -u film/kit/make.py --all --batch library --engine auto --skip narrate
python3 film/kit/publish.py --batch library --voice-only 2>/dev/null || python3 film/kit/publish.py --batch library --nobed
python3 film/kit/publish.py --batch fy27 --voice-only 2>/dev/null || python3 film/kit/publish.py --batch fy27 --nobed
echo FINAL2 DONE
