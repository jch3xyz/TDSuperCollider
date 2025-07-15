// scripts/introspect-synthdefs.scd

"Introspecting user synthDefs…".postln;

~mySynthNames.do { |synthName|
	var desc, controls, params;

    desc = SynthDescLib.global[synthName.asSymbol];
    if(desc.notNil) {
        // get just the control names
        controls = desc.controls
                           .collect({ |c| c.name.asString });
        params   = controls.join(",");
        ~td.sendMsg("/synthDef", synthName, params);
		//(synthName ++ params).postln;
    } {
        ("% not found in SynthDescLib").format(synthName).postln;
    };
};

"Done sending synthDef list.".postln;

//SynthDescLib.global.browse
//~mySynthNames.postln

//SynthDescLib.global[\simpleSine].controls