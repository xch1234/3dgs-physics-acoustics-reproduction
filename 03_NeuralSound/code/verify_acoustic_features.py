"""Cross-check local encoded samples against the unmodified author dataset."""
import json
from pathlib import Path
import numpy as np
from train_radiation import Maps
from acoustic.dataset import AcousticDatasetFar

ROOT=Path(__file__).resolve().parents[1]


def main():
    folder=ROOT/'inputs/procedural_bempp'
    records=[]
    for phase in ('train','val','test'):
        original=AcousticDatasetFar(str(folder),phase)
        local=Maps(phase,True,folder)
        for index in (0,len(original)-1):
            for seed in (101,502):
                np.random.seed(seed)
                mode=int(np.random.randint(len(local.data[index]['freqs'])))
                after_selection=np.random.get_state()
                np.random.seed(seed)
                expected=original[index]
                np.random.set_state(after_selection)
                actual=local[local.samples.index((index,mode))]
                assert np.array_equal(expected[0],actual[0])
                errors=[float(np.max(np.abs(np.asarray(a)-np.asarray(b)))) for a,b in zip(expected[1:4],actual[1:4])]
                assert max(errors)<1e-6,errors
                records.append(dict(phase=phase,geometry=index,mode=mode,seed=seed,max_absolute_errors=errors))
    result=dict(passed=True,records=records,
        scope='same modal sample and same augmentation RNG: coordinates, all 23 features, normalized FFAT and log-amplitude compared with original AcousticDatasetFar',
        sampling_difference='author dataset samples one random mode per geometry item; local dataset enumerates all six modes as separate items before shuffle/drop_last')
    (ROOT/'docs/acoustic-feature-contract.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
