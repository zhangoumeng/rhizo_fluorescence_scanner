const byte numChars = 32;
char receivedChars[numChars];   // an array to store the received data

int newData = 0;

int val = 0;             // new for this version
int x;

void setup() {
    Serial.begin(9600);
    Serial.println("<Arduino is ready>");
    pinMode(6,OUTPUT); // set Pin6 as PUL for x
    pinMode(7,OUTPUT); // set Pin7 as DIR for x
    pinMode(9,OUTPUT); // set Pin9 as PUL for y
    pinMode(8,OUTPUT); // set Pin8 as DIR for y
    pinMode(11,OUTPUT); // set Pin11 as LED
    pinMode(12,OUTPUT); // set Pin12 as LED
}

void loop() {
    recvWithEndMarker();
    showNewNumber();
}

void recvWithEndMarker() {
    static byte ndx = 0;
    char endMarker1 = 'x';
    char endMarker2 = 'y';
    char endMarker3 = 'a';
    char endMarker4 = 'b';
    char endMarker5 = 'c';
    char endMarker6 = 'd';
    char rc;
    
    if (Serial.available() > 0) {
        rc = Serial.read();

        if (rc == endMarker1) {
            receivedChars[ndx] = '\0'; // terminate the string
            ndx = 0;
            newData = 1;
        }
        else if (rc == endMarker2) {
            receivedChars[ndx] = '\0'; // terminate the string
            ndx = 0;
            newData = 2;
        }
        else if (rc == endMarker3) {
            digitalWrite(12,HIGH);
        }
        else if (rc == endMarker4) {
            digitalWrite(12,LOW);
        }
        else if (rc == endMarker5) {
            digitalWrite(11,HIGH);
        }
        else if (rc == endMarker6) {
            digitalWrite(11,LOW);
        }
        else {
            receivedChars[ndx] = rc;
            ndx++;
            if (ndx >= numChars) {
                ndx = numChars - 1;
            }
        }
    }
}

void showNewNumber() {
    if (newData == 1) {
        val = 0;             // new for this version
        val = atoi(receivedChars);   // new for this version
        newData = false;
        if (val>0){
          digitalWrite(7,HIGH);
        }
        else{
          digitalWrite(7,LOW); // set high level direction
          val = -val;
        }
        for(x = 0; x < val; x++){
          digitalWrite(6,HIGH); // Output high
          delayMicroseconds(1000); // set rotate speed
          digitalWrite(6,LOW); // Output low
          delayMicroseconds(1000); // set rotate speed
          }
    }
    if (newData == 2) {
        val = 0;             // new for this version
        val = atoi(receivedChars);   // new for this version
        newData = false;
        if (val>0){
          digitalWrite(8,HIGH);
        }
        else{
          digitalWrite(8,LOW); // set high level direction
          val = -val;
        }
        for(x = 0; x < val; x++){
          digitalWrite(9,HIGH); // Output high
          delayMicroseconds(1000); // set rotate speed
          digitalWrite(9,LOW); // Output low
          delayMicroseconds(1000); // set rotate speed
          }
    }
}

