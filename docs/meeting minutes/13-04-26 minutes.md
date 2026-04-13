## Minutes of Meeting 13.04.2026

Notes taken by: De Qi

Present (Exactum): Teemu, Ceren, De Qi, Tom, Tuula

### Minutes:
1. Tom's progress
    - EQTransformer and EQCCT produced 102 and 152 predictions (false positives) respectively on 2000 noise waveforms.
    - Hard to find missed events using visual inspection of the filtered noise waveforms
    - Noise waveforms produce very obvious delta error modes for P and S picks, but distributions are not very gaussian for both. A spike in -1.0s delta for P-picks, and right skewed distribution for S picks.
    - Stations from FN network seem to exhibit a pattern where the delta error is around 1.0s for S-picks
    - EQBlocklyTransformer setup still WIP, but have successfully fine-tuned model on example data provided in the EQBlocklyTransfomer repository
    - Have asked the client if there are possible reasons why S predictions for earthquakes were generally late for both EQTransfomer and EQCCTPro, waiting for reply

2. Teemu's progress
    - Edited EQCCTPro and seisbench classes to extract probability traces and generate their image PNG files
    - Create API in EQCCTPro and seisbench to allow user to select via indices waveforms to run predictions
    - EQTransformer observed to provides many (around 4) P-pick probability spikes 
    - Some visually obvious P picks (station KLF) did not exceed the probability threshold (<0.1) and thus not detected by EQCCTPro, but EQTransformer showed high probability spike (>0.9) 

3. Ceren's progress
   - S pick detector misses S picks, metrics are worse than P pick
   - Did not run on all waveforms due to some channels missing
   - Sent client STA/LTA code for checking, still waiting for them to reply
   - Used obspy to achieve the best metrics, but the threshold parameters were completely different from ISUH's 
   - Very difficult to perfectly replicate client's STA/LTA given limited information. Will explain the development process of STA/LTA for the report. Obspy metrics will be used as the baseline metric.
   - Tuula's suggestion to use client's STA/LTA historical performance metrics as the comparison baseline as a fallback.

4. TODO:
    - Final presentation slides
        - [Deqi] pitch (1 slide):
        - technical (5-6 slides):
            - [Deqi] 1 slide for p wave and s wave explanation
            - [Deqi] 1 slide for data extraction, diagram of tasks 
            - [Teemu] 2 slides for eqtransformer and eqcct 
            - [Ceren] 1 slide for STA/LTA: custom model and obspy
            - [Tom] 1 slide for model results
        - reflection and conclusion (2-3 slides):
            - [Tom] Challenges (1 slide): 
                - Unexplained phenomenon for S picks being later on average for earthquakes
                - Client's STA/LTA almost impossible to replicate
            - [Tuula] rest of the reflections (2 slides):
                - Client's original goal has changed. Instead of configuring EQCCTPro for real-time detection, it is now exploring eqtransformer, because the former does not offer training pipeline.
                - How would you do the project differently?
        

5. Upcoming tasks:
    - 21.04.2026: Final Presentation
    - 15.05.2026: Final Report submission

### Upcoming:
- Team project meeting: **Mon 20.04.2026 at 10:00, Exactum A318**