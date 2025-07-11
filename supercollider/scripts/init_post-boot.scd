~makeNodes = {
    ~srcGroup = Group();
    ~fxGroup = Group(~srcGroup, \addAfter);
    ~reverb = Synth(\reverb, [in: ~fxBus, mix: 0.1], ~fxGroup);
};

ServerTree.add(~makeNodes);
ServerTree.run;