(
var quarkURL = "https://github.com/jch3xyz/ChordSymbol2.git";

if (Quarks.isInstalled("ChordSymbol")) {
    "ChordSymbol2 already installed".postln;
} {
    Quarks.install(quarkURL);
    "Installed ChordSymbol2".postln;
}
)