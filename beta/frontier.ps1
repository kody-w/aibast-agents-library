Write-Output "RAPP Brainstem Frontier has been retired. To build from scratch on your own device, install the Brainstem:"
Write-Output "irm https://microsoft.github.io/aibast-agents-library/install.ps1 | iex"
# throw, not exit: under "irm ... | iex" exit would close the window before the message can be read.
throw "RAPP Brainstem Frontier has been retired."
