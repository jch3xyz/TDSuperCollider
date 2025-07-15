//simple sine wave mainly for testing

SynthDef(\simpleSine, { |freq=440, lpFreq=5000, vol=0.5|
    var sig;
    sig = SinOsc.ar(freq) * vol;
    sig = LPF.ar(sig, lpFreq);
    Out.ar(0, sig!2);
}).add;


thisProcess.nowExecutingPath