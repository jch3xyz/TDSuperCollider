(
// ---------- MASTER STARTUP SCRIPT ----------

"Running TDSuperCollider.scd...".postln;

~basePath = thisProcess.nowExecutingPath.dirname;

// define TD reply address *first*
~td = NetAddr("127.0.0.1", 8000);

// Pre-boot setup
"Loading init_pre-boot.scd...".postln;
this.executeFile(~basePath +/+ "scripts/init_pre-boot.scd");

//Install Quarks
this.executeFile(~basePath +/+ "scripts/install-quarks.scd");

// Boot the server
s.waitForBoot({

	~mySynthNames = IdentitySet.new;

    // Load SynthDefs
    "Loading synthdefs...".postln;
    PathName(~basePath +/+ "synthdefs").entries.do { |file|
        if(file.extension == "scd") {
            //file.fullPath.postln;
            this.executeFile(file.fullPath);
			~mySynthNames.add(file.fileNameWithoutExtension);
        };
    };

	// introspection step
    this.executeFile(~basePath +/+ "scripts/introspect-synthdefs.scd");

	// Load OSCDefs
	"Loading oscdefs...".postln;
    PathName(~basePath +/+ "oscdefs").entries.do { |file|
        if(file.extension == "scd") {
            //file.fullPath.postln;
            this.executeFile(file.fullPath);
        };
    };

    // Post-boot setup
   // "Loading init_post-boot.scd...".postln;
    //this.executeFile(~basePath +/+ "scripts/init_post-boot.scd");

	// print pid for python to parse and store
	SystemClock.sched(0.1, {
		("pid: " ++ s.pid).postln;
	});

    // Send langPort back to TouchDesigner
    ~td.sendMsg("/sc/port", NetAddr.langPort);
	"Booted.".postln;

	SystemClock.sched(0.2, {
		"TDSuperCollider is ready to use!".postln;
	});
});
)



//OSCFunc.trace(false)

//NetAddr.langPort

