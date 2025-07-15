(
var quarkURL = "https://github.com/triss/ChordSymbol.git";

if (Quarks.isInstalled("ChordSymbol")) {
    "ChordSymbol already installed".postln;
} {
    Quarks.install(quarkURL);
    "Installed ChordSymbol".postln;
}
)