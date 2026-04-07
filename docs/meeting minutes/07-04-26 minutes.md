## Minutes of Meeting 07.04.2026

Notes taken by: De Qi

Present (Exactum): Teemu, De Qi, Tom, Tuula

### Minutes:
1. De Qi's progress
- Deleted mistake event waveform from the noise dataset 

2. Tom's progress
- Gnerated metrics for earthquakes and explosions for both EQTransformer and EQCCTPro
- EQTransfomer has slightly better performance than EQCCTPro on earthquakes. Metrics have been pushed to github.
- Was able to format data file structure suitable for BlocklyEQTransfomer, but ran into config issues when running inference.
- Plotted arrival time differences for EQTransformer and EQCCTPro for earthquakes and explosions. For earthquakes for both models, although P picks had a symmetric distribution about zero error, S picks had more late predictions, causing the distribution to be heavier on the right. In contrast, error distributions for both P and S picks for both models were rather symmetric for explosions.

3. Teemu's progress
- Have launched BlocklyEQTransfomer UI and demoed the fine-tuning of an example model during the meeting

4. Ceren's progress
   - Sent client STA/LTA code for checking, waiting for them to reply

5. TODO:
    - Use BlocklyEQTransfomer to fine-tune of the pre-trained EQTransformer
    - Plot arrival time differences with different deltas
    - Ask the client if there are possible reasons why S predictions for earthquakes were generally late for both EQTransfomer and EQCCTPro
    - Start writing final report maybe

6. Upcoming tasks:
    - 21.04.2026: Final Presentation
    - 15.05.2026: Final Report submission

### Upcoming:
- Team project meeting: **Mon 13.04.2026 at 10:00, Exactum A318**