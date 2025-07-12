//OSCdef(\tdSynth).free;

(
// SimpleSine2.scd
// Defines \simpleSine and a bidirectional OSC protocol on "/synth".
// Assumes the server is already booted by your startup script.

/////////////////////
// 1) SynthDef
/////////////////////
SynthDef(\simpleSine, { |freq=440, lpFreq=5000, vol=0.5|
    var sig;
    sig = SinOsc.ar(freq) * vol;
    sig = LPF.ar(sig, lpFreq);
    Out.ar(0, sig!2);
}).add;

/////////////////////
// 2) OSC handler
/////////////////////
OSCdef.new(
    \tdSynth,                     // internal name
    { |msg, time, addr|           // callback
        // — declare all vars up front —
        var synthType, action, data, kv;
        var name, freqs, args, node, nodeID, resp, key, i;

        // parse header
        synthType = msg[1].asSymbol;
        action    = msg[2].asString;

        // build key/value Dictionary
        data = msg.copyRange(3, msg.size - 1);
        kv   = Dictionary.new;
        i = 0;
        while({ i < data.size }, {
            key = data[i];
            key = if(key.isString, { key }, { key.asString });
            kv[key] = data[i + 1];
            i = i + 2;
        });

        // dispatch based on action
        switch(action,

            // PLAY: spawn one Synth per freq
            "play", {
                name = kv.at("name");
                freqs = if(kv.at("freq").notNil,
                    { [ kv.at("freq") ].flat },
                    { [ nil ] }
                );

                freqs.do({ |f|
                    // build SC args (\freq, f plus extras)
                    args = [ \freq, f ];
                    kv.keys.do({ |k|
                        if(k != "name" and: { k != "freq" }) {
                            args = args ++ [ k.asSymbol, kv[k] ];
                        };
                    });

                    // spawn synth (SC assigns nodeID)
                    node = Synth(synthType, args);

                    // reply with "created"
                    resp = [
                        synthType.asString,
                        node.nodeID,
                        "created",
                        "name", name,
                        "freq", f
                    ];
                    kv.keys.do({ |k|
                        if(k != "name" and: { k != "freq" }) {
                            resp = resp ++ [ k, kv[k] ];
                        };
                    });
                    ~td.sendMsg("/synth", *resp);
                });
            },

            // UPDATE: set params on an existing node
            "update", {
                nodeID = kv.at("id");
                node   = Node(nodeID);
                kv.keys.do({ |k|
                    if(k != "id") {
                        node.set(k.asSymbol, kv[k]);
                    };
                });
                // acknowledge update
                resp = [ synthType.asString, nodeID, "updated" ];
                kv.keys.do({ |k|
                    if(k != "id") {
                        resp = resp ++ [ k, kv[k] ];
                    };
                });
                ~td.sendMsg("/synth", *resp);
            },

            // KILL: free the node
            "kill", {
                nodeID = kv.at("id");
                node   = Node(nodeID);
                s.sendMsg("/n_free", nodeID);
               ~td.sendMsg("/synth", synthType.asString, nodeID, "killed");
            },

            // UNKNOWN action
            {
                ("[tdSynth] Unknown action: " ++ action).postln;
            }
        );
    },
    "/synth"                       // OSC address to listen on
);
)
