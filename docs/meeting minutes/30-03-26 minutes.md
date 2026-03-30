## Minutes of Meeting 30.03.2026

Notes taken by: De Qi

Present (Exactum): Teemu, De Qi, Tom, Ceren, Tuula

### Minutes:
1. De Qi's progress 
    - Plot kurtosis on noise and event waveforms and visualise boxplots.
    - Will delete one waveform from the dataset that was included by mistake, but keep the rest of the noise waveforms for visualisations in the report.

2. Tom's progress
    -  Used 0.5s delta to obtain results for all events and noise waveforms and plotted histograms for their prediction error time
    - recall and precision drops to 0.21, 0.61, 0.11, 0.54, for p picks and s picks for explosions respectively
    - Could be that eqcct does not generalise well to finnish earthquakes

3. Teemu's progress
    - Has run EQTransformer, producing results that can be visualised


4. Ceren's progress
   - Implemented STALTA in obspy just to explore different methods to see if there could be performance improvements, but obspy's STA/LTA does not allow client's additional parameters to be incorporated
   - The first STA/LTA that Ceren implemented still had the best metrics

5. TODO:
    - Tom to configure dataset for EQTransformer
    - Ceren to share the various STA/LTA implementations with the client for verification before the easter break


6. Upcoming tasks:
    - 21.04.2026: Final Presentation
    - 15.05.2026: Final Report submission

### Upcoming:
- Team project meeting: **Tue 07.04.2026 at 12:00, Exactum**