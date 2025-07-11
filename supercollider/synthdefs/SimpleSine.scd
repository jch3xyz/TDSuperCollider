// simpleSine.scd

SynthDef(\simpleSine, { |out=0, freq=440, lpFreq=8000, vol=0.5, gate=1|
    var sig, env;
    sig = SinOsc.ar(freq);
    sig = LPF.ar(sig, lpFreq);
    env = Env.asr(0.01, 1, 0.3).ar(gate, doneAction:2);
    Out.ar(out, sig * env * vol);
}).add;

// Paired OSCdef
~synths = ~synths ?? { IdentityDictionary.new };

OSCdef(\sineRouter, { |msg, time, addr, recvPort|

    var cmd, id, synth, i;

    cmd = msg[1];

    switch(cmd,

        // -------- play --------
        'play', {
            synth = Synth(\simpleSine, [
                \freq,   msg[2],
                \lpFreq, msg[3],
                \vol,    msg[4]
            ]);
            ~synths[synth.nodeID] = synth;
            addr.sendMsg('/sine/played', synth.nodeID, msg[2], msg[3], msg[4]);
        },

        // -------- set ---------
        'set', {
            id    = msg[2];
            synth = ~synths[id];
            i     = 3;
            if(synth.notNil) {
                while { i < msg.size } {
                    synth.set(msg[i], msg[i+1]);
                    i = i + 2;
                };
                addr.sendMsg('/sine/updated', id);
            };
        },

        // -------- kill --------
        'kill', {
            id    = msg[2];
            synth = ~synths.removeAt(id);
            if(synth.notNil) {
                synth.set(\gate, 0);
                synth.free;
                addr.sendMsg('/sine/killed', id);
            };
        }
    );
}, '/sine');