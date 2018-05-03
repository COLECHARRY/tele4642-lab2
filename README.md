###TELE4642 - Lab2

#### Mininet

Mininet Fat Tree Topology defined in main.py as ftt()

Init either by running ```python main.py``` or ```sudo mn --custom main.py --topo ftt --controller=remote --arp```


#### Ryu Application

Ryu Application in ryuapp.py

Run by ```ryu-manager ryuapp.py (--verbose)```

Ommit --verbose flag if you don't want to see messages

#### Other stuff

Test files are basic code setups used for testing API interactions

routemanager.py is a REST API implementation of the Fat Tree routing table (partially incomplete)

Run with ```ryu-manager ryu.app.ofctl_rest --verbose``` and ```python routemanager.py```
