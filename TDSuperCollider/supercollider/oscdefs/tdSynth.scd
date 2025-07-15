// handles all incoming messages with address "/synth" and routes them to the correct synthdef. Also sends OSC messages back to TouchDesigner

OSCdef.new(
    \tdSynth,                     // internal name
    { |msg, time, addr|           // callback
        // — declare all vars up front —
        var synthType, action, data, kv;
        var name, freqs, args, node, nodeID, resp, key, i, raw, evaluated, rawFreq;

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
                rawFreq = kv.at("freq");
				freqs = if(
					rawFreq.notNil,
					{
						[ rawFreq ].flat.collect { |raw|
							raw.isKindOf(Symbol).if(
								{ raw.asString.interpret },  // evaluate any string
								{ raw }
							)             // otherwise leave it as-is
						}
					},
					{ [ nil ] }
				).flat;

                freqs.do({ |f|
                    // build SC args (\freq, f plus extras)
                    args = [ \freq, f ];
                    kv.keys.do({ |k|
                        if(k != "name" and: { k != "freq" }) {
							raw = kv[k];
							// if the value is a String, interpret as SC code, otherwise use raw value
							evaluated = raw.isKindOf(Symbol).if({ raw.asString.interpret }, { raw });
                            args = args ++ [ k.asSymbol, evaluated ].flat;
                        };
                    });

                    // spawn synth (SC assigns nodeID)
                    node = Synth(synthType, args);


					// then register an onFree handler
					node.onFree({
						("free: " + node.nodeID).postln;
						// fire the exact same OSC you’d get from your manual /synth "kill"
						~td.sendMsg('/synth',
							synthType.asString,
							node.nodeID,
							"killed")
					});

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
							raw = kv[k];
							// if the value is a String, interpret as SC code, otherwise use raw value
							evaluated = raw.isKindOf(Symbol).if({ raw.asString.interpret }, { raw });
                            resp = resp ++ [ k, evaluated ];
                        };
                    });
                    ~td.sendMsg("/synth", *resp);
                });
            },

            // UPDATE: set params on an existing node
            "update", {
                nodeID = kv.at("id");
                kv.keys.do({ |k|
                    if(k != "id") {
						raw = kv[k];
						// if the value is a String, interpret as SC code, otherwise use raw value
						evaluated = raw.isKindOf(Symbol).if({ raw.asString.interpret }, { raw });
                        // this sends directly on the default server
						s.sendMsg("/n_set", nodeID, k.asSymbol, evaluated);
                    };
                });
                // acknowledge update
                resp = [ synthType.asString, nodeID, "updated" ];
                kv.keys.do({ |k|
                    if(k != "id") {
						raw = kv[k];
						// if the value is a String, interpret as SC code, otherwise use raw value
						evaluated = raw.isKindOf(Symbol).if({ raw.asString.interpret }, { raw });
                        resp = resp ++ [ k, evaluated ];
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

