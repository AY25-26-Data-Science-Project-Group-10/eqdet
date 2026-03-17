## Minutes of Meeting 17.03.2026

Notes taken by: De Qi, Tom

Present: Matt Gardine (ISUH), Amir Sadeghi-Bagherabadi (ISUH), Teemu, De Qi, Tom, Ceren, Tuula, 


### Minutes:
These are discussion points not covered in the slides sent by Matt.t 
1. Project details:
    - Next steps: Evaluate EQCCTPro against EQTransformer because:
        - EQTransformer's training pipeline is exposed, allowing us to train it on Finnish seismic events, which have a much lower magnitude than the datasets EQCCTPro was trained on.
        - EQTransformer was found to perform better than PhaseNet, so EQTransformer will be the next best baseline to compare against. 
    - Client's wishes for the documentation
      - EQCCTPro's filtering method
      - Stastistics on number of triggers by STALTA
      - Histogram of time difference between predicted picks and manual picks
      - Probability traces of EQCCTPro
    - STA/LTA
      - Client uses the earliest trigger as the phase arrival time, instead of our current implementation where the trigger with the highest ratio is chosen.
      - Extremely difficult to replicate client's pick selection process from STA/LTA triggers because the real mechanism involves comparing waveform between multiple stations for each event. In addition, some picks are manually adjusted to fit the known distance of the station from the earthquake instead of looking at the waveform. 
      - Client usually gets ~100 triggers for one earthquake
    - Metrics
      - 2s delta is too big to differentiate TP and FP. 1s is preferred. 
    - EQCCTPro
      - EQCCTPro was observed to throw errors for some waveforms because their sampling frequencies were too low (<100Hz) for the model's requirements. This was caused by the use of the BH* channel (10-80Hz) of stations in the FN network, instead of the needed \*H\* channel (80-250Hz). The operators of these stations have yet to migrate to hardware which supports \*H\* channels.
      - Client would like us to ignore waveforms from these channels.
    - Clarifications
      - Classification of earthquakes and explosions are not required
      - Client is ok with not using the probable_explosions events
    

2. More background knowledge:
    - How to differentiate between explosions and earthquakes
      - Explosions typically have p waves that move upwards first, but earthquakes can move in any direction.
      - Typically differentiated by plotting the the waveforms' fast fourier transforms against time plots and looking for differentiated frequency bands.
    - Pick selection
      - When making the final picks, the human analyst only looks at triggered waveforms, does not scan the entire waveform. This creates false negatives. 

### Upcoming:
- Team project meeting: **Monday 23.03.2026 at 10:00, Exactum**
- Final presentation: **21.04.2026**
- Final report submission deadline: **15.05.2026**