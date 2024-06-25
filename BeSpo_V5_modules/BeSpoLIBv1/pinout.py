Midi out - GP0
LED - GP2
There are 64 step leds and
then there will be 4 for the mute idication
4 for the velocity,
one for play, another for pitch bend feedback(green for plus, red for -)
16 for the pattern select indicator.

Stemma I2C is preconfigures as such. (GP4 and GP5)

input matrix
Cols 1-8 are GP6 to GP13
Rows are GP14 to GP22, and GP26 to GP28. The matrix I/O configururation is set up as before.
the first 8 rows are the step seuencer grid. 1 and 2 being voice 1, ro3 and 4 are voice two...
These are are latching and will represent teh first 64leds.
the next four rows id like to assign the mute to the first col and each row respective to the voice rows
the next col would be the clear buttons (momentary)
the next col would be the velocity buttons (momentary)
tne next col would be the voice down buttons
the next row would be the voice up buttons
the next would be the pattern selct button
the next would be the shuffle +, shuffle -, pitch bend up, pitch bend down
the next would be play. the three left we can adjust as neccsary.
Please label the LED number in the comments of each fucntion.
