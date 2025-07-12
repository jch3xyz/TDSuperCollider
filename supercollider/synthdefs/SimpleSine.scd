// simpleSine.scd

// 1) SynthDef unchanged
SynthDef(\simpleSine, { |out=0, freq=440, lpFreq=8000, vol=0.5, gate=1|
    var sig, env;
    sig = SinOsc.ar(freq);
    sig = LPF.ar(sig, lpFreq);
    env = Env.asr(0.01, 1, 0.3).ar(gate, doneAction:2);
    Out.ar(out, sig * env * vol);
}).add;

// 2) Global storage for instances
~synths = ~synths ?? { IdentityDictionary.new };

// 3) Single OSCdef for all synths
OSCdef(\synthRouter, { |msg, time, addr|
    // declare all locals up front
    var synthType, action, id, synth, freq, cutoff, volume, param, value;

    // parse incoming
    synthType = msg[1].asString;        // e.g. "simpleSine"
    action    = msg[2].asString;        // "play" / "update" / "kill"

	msg.postln;

	// ignore other synths
   if (synthType == "simpleSine", {

		//("got type: " ++ synthType).postln;

		switch(action,

			// ——— play → create instance
			"play", {
				freq   = msg[3];
				cutoff = msg[4];
				volume = msg[5];

				synth = Synth(\simpleSine, [
					\freq,   freq,
					\lpFreq, cutoff,
					\vol,    volume
				]);

				~synths[synth.nodeID] = synth;

				// notify TD: [ type, id, event, param/value… ]
				~td.sendMsg(
					"/synth",
					 \simpleSine,
						synth.nodeID,
						\created,
						\freq,   freq,
						\lpFreq, cutoff,
						\vol,    volume
				);
			},

			// ——— update → change params
			"update", {
				id    = msg[3];
				param = msg[4];
				value = msg[5];

				synth = ~synths[id];
				if(synth.notNil) {
					synth.set(param.asSymbol, value);
					~td.sendMsg(
						"/synth",
						 \simpleSine,
							id,
							\updated,
							param, value
					);
				};
			},

			// ——— kill → free instance
			"kill", {
				id    = msg[3];
				synth = ~synths.removeAt(id);
				if(synth.notNil) {
					synth.free;
					~td.sendMsg(
						"/synth",
						\simpleSine,
							id,
							\killed
					);
				};
			}

		);
	});
}, "/synth");