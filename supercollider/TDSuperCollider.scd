(
// ---------- MASTER STARTUP SCRIPT ----------

"Running TDSuperCollider.scd...".postln;

~basePath = thisProcess.nowExecutingPath.dirname;

// define TD reply address *first*
~td = NetAddr("127.0.0.1", 8000);

// Pre-boot setup
"Loading init_pre-boot.scd...".postln;
this.executeFile(~basePath +/+ "scripts/init_pre-boot.scd");

// Boot the server
s.waitForBoot({
    // Load SynthDefs and OSCDefs
    "Booted. Loading synthdefs...".postln;
    PathName(~basePath +/+ "synthdefs").entries.do { |file|
        if(file.extension == "scd") {
            file.fullPath.postln;
            this.executeFile(file.fullPath);
        };
    };

    // Post-boot setup
   // "Loading init_post-boot.scd...".postln;
    //this.executeFile(~basePath +/+ "scripts/init_post-boot.scd");

    // Send langPort back to TouchDesigner
    ~td.sendMsg("/sc/port", NetAddr.langPort);
});
)

//OSCFunc.trace(false)

//NetAddr.langPort

