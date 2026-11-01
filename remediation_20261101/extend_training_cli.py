from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[1];p=R/'03_NeuralSound/code/train_radiation.py';backup=R/'remediation_20261101/backups/train_radiation.py';shutil.copy2(p,backup);s=p.read_text(encoding='utf8')
s=s.replace("parser.add_argument('--resume',action='store_true');args=parser.parse_args()", """parser.add_argument('--output-dir',type=Path)
    parser.add_argument('--checkpoint-dir',type=Path)
    parser.add_argument('--input-dir',type=Path)
    parser.add_argument('--no-augmentation',action='store_true')
    parser.add_argument('--learning-rate',type=float)
    parser.add_argument('--decay-period',type=int)
    parser.add_argument('--decay-factor',type=float)
    parser.add_argument('--seed',type=int,default=20261102)
    parser.add_argument('--resume',action='store_true');args=parser.parse_args()""")
s=s.replace('np.random.seed(20261102);torch.manual_seed(20261102);torch.cuda.manual_seed_all(20261102)', '''if args.learning_rate is not None:learning_rate=args.learning_rate
    if args.decay_period is not None:decay_period=args.decay_period
    if args.decay_factor is not None:decay_factor=args.decay_factor
    np.random.seed(args.seed);torch.manual_seed(args.seed);torch.cuda.manual_seed_all(args.seed)''')
s=s.replace("out=ROOT/'outputs'/('radiation_paper_schedule' if args.paper_schedule else 'radiation_training');", "out=args.output_dir or ROOT/'outputs'/('radiation_paper_schedule' if args.paper_schedule else 'radiation_training');")
s=s.replace("checkpoint_dir=out/'checkpoints' if args.paper_schedule else Path('/opt/3dgs-runtime/checkpoints/neuralsound-radiation')", "checkpoint_dir=args.checkpoint_dir or (out/'checkpoints' if args.output_dir or args.paper_schedule else Path('/opt/3dgs-runtime/checkpoints/neuralsound-radiation'))")
s=s.replace("train=Maps('train',True);val=Maps('val');test=Maps('test')", "train=Maps('train',not args.no_augmentation,folder=args.input_dir);val=Maps('val',folder=args.input_dir);test=Maps('test',folder=args.input_dir)")
s=s.replace("'training_settings=dict('","'training_settings=dict('") # no semantic change
s=s.replace("training_settings=dict(initial_learning_rate=learning_rate,", "training_settings=dict(seed=args.seed,augmentation=not args.no_augmentation,input_dir=str(args.input_dir) if args.input_dir else None,initial_learning_rate=learning_rate,")
s=s.replace("(ROOT/'docs'/metric_name).write_text(payload)", "(out/metric_name if args.output_dir else ROOT/'docs'/metric_name).write_text(payload)")
p.write_text(s,encoding='utf8')
print('Radiation runner now supports isolated outputs/checkpoints and explicit training controls; default settings preserved')
