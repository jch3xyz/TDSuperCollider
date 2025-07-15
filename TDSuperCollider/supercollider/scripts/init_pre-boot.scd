// init_pre-boot.scd

s.options.sampleRate = 48000;
s.options.numOutputBusChannels = 2;

s.newBusAllocators;
~fxBus = Bus.audio(s, 2);

~cleanup = {
    s.freeAll;
    ServerBoot.removeAll;
    ServerTree.removeAll;
    ServerQuit.removeAll;
    OSCdef.freeAll;
    "Cleaned up server.".postln;
};

~cleanup.();  // clean on boot
ServerQuit.add(~cleanup);