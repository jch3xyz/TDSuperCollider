// Companion Code 9.1: Post-Boot Setup
// A Template for Large-Scale Projects

// This sub-file handles initialization tasks meant to occur after the server has booted and other server-related tasks are complete. Populating the server with Synths and Groups is perhaps the most likely action to occur here. Note that we should not register ~makeNodes with ServerTree in the pre-boot sub-file. If we did, SC would attempt to create a reverb Synth immediately after the server boots, before the reverb SynthDef is fully built. Instead, these actions should be the last setup task to occur, guaranteeing that the processes they depend on are complete.

~makeNodes = {
	~srcGroup = Group();
	~fxGroup = Group(~srcGroup, \addAfter);
	~reverb = Synth(\reverb, [in: ~fxBus, mix: 0.1], ~fxGroup);
};

ServerTree.add(~makeNodes);
ServerTree.run;