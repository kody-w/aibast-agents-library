cd /Users/kodywildfeuer/Documents/GitHub/aibast-agents-library
export FILM_SPEECH_RESOURCE_ID="/subscriptions/14d18b0c-2dd3-4e69-a8bf-641d32368046/resourceGroups/koda-ai/providers/Microsoft.CognitiveServices/accounts/koda-speech"
for s in customer-service-case-intelligence-d365 editorial-story-discovery-and-market-intelligence frontline-coaching-1-1-documentation industrial-asset-reliability-and-engineering-standards industry-compliance-and-risk-monitoring requirements-and-innovation-authoring; do
  echo "=== $s ==="
  python3 -u film/kit/make.py --project "$s" --engine auto
done
echo FIXUP DONE
