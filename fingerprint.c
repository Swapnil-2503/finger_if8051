#include <p89v51rd2.h>
#include "FINGER_DEF.h"

#define FOSC 16000000UL
#define BAUD 9600



//------------------------------------
// UART Initialization
//------------------------------------
void UART_Init(void)
{
    SCON = 0x50;
    /*
        SM0 = 0
        SM1 = 1  -> UART Mode 1 (8-bit UART)
        REN = 1  -> Enable Receiver
    */

    TMOD &= 0x0F;   // Clear Timer1 bits
    TMOD |= 0x20;   // Timer1 Mode2 (8-bit auto reload)

    PCON &= 0x7F;   // SMOD = 0 (normal baudrate)

    /*
        Baudrate calculation:

        TH1 = 256 - (FOSC / (384 * BAUD))

        For 16MHz and 9600 baud:

        TH1 = 256 - (16000000 / (384 * 9600))
             = 256 - 4.34
             = 252
             = 0xFC
    */

    TH1 = 0xFC;
    TL1 = 0xFC;

    TR1 = 1;    // Start Timer1
}

//------------------------------------
// UART Transmit Character
//------------------------------------
void UART_TxChar(char ch)
{
    SBUF = ch;

    while(TI == 0);

    TI = 0;
}

//------------------------------------
// UART Transmit String
//------------------------------------
void UART_TxString(char *str)
{
    while(*str)
    {
        UART_TxChar(*str++);
    }
}

void UART_TxArray(unsigned char *arr, unsigned int len)
{
    unsigned int i;

    for(i = 0; i < len; i++)
    {
        UART_TxChar(arr[i]);
    }
}
//------------------------------------
// UART Receive Character
//------------------------------------
char UART_RxChar(void)
{
    while(RI == 0);

    RI = 0;

    return SBUF;
}

void Delay(unsigned int ms)
{
    unsigned int i,j;

    for(i = 0; i < ms; i++)
    {
        for(j = 0; j < 1275; j++);
    }
}

//------------------------------------
// Enroll Fingerprint Function
//------------------------------------
void EnrollFinger(void)
{
    unsigned char i;

    UART_TxString("Place Finger First Time\r\n");

    Delay(3000);

    // Capture Finger
    UART_TxArray(GenImg,12);

    Delay(1000);

    // Convert to Buffer1
    UART_TxArray(Img2Tz1,13);

    Delay(1000);

    UART_TxString("Remove Finger\r\n");

    Delay(3000);

    UART_TxString("Place Same Finger Again\r\n");

    Delay(3000);

    // Capture Again
    UART_TxArray(GenImg,12);

    Delay(1000);

    // Convert to Buffer2
    UART_TxArray(Img2Tz2,13);

    Delay(1000);

    // Create Template
    UART_TxArray(RegModel,12);

    Delay(1000);

    // Store Template
    UART_TxArray(Store,15);

    Delay(1000);

    UART_TxString("Fingerprint Stored\r\n");
}

//------------------------------------
// Main
//------------------------------------
void main(void)
{
    UART_Init();

    UART_TxString("R307 Fingerprint System\r\n");

    Delay(2000);

    EnrollFinger();

    while(1)
    {

    }
}