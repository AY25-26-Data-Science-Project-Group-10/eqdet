## Minutes of Meeting 09.02.2026

Notes taken by: Ceren, De Qi

Present: Teemu, De Qi, Tom, Ceren, Tuula

- Save minutes from every meeting to the project GitHub repository.

### Minutes:
1. Deqi's progress
    - Geographic visualisation of events from QuakeML files sent by Matt
    - Queried miniseed data and station data from ISUH IP address. ISUH IP address found to not provide event data (P and S picks)
    - Can run EQCCTOne inference on device

2. Tom's progress
    - Successfully cloned EQCCTPro
    - Ran waveform filtering using obspy

3. Teemu's progress
    - Successfully ran EQCCTPro, problem with weights suspected to be a pipeline issue, temporary fix using suggestions from LLM. 
    - Found that weights in EQCCTPro are not updated, because running inference on it throws error
    - Found that `create_dataset()` function from EQCCTPro can help in formatting waveform data for inference

4. TODO:
- Build waveform dataset from ISUH IP address, ensuring there are noise-only waveforms
- Figure out how to run EQCCTPro
- More visualisations of Matt's quakeML files
- Start working on STA/LTA code for benchmarking

### Upcoming:
- Team project meeting: **Monday 16.02.2026 at 10:00, Exactum**