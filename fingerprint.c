#include <p89v51rd2.h>
#include "FINGER_DEF.h"

#define FOSC 16000000UL
#define BAUD 9600

unsigned char RxBuf[20];

//------------------------------------
// UART Initialization
//------------------------------------
void UART_Init(void)
{
    SCON = 0x50;

    TMOD &= 0x0F;
    TMOD |= 0x20;

    PCON &= 0x7F;

    TH1 = 0xFC;
    TL1 = 0xFC;

    TR1 = 1;
}

//------------------------------------
// UART Transmit Character
//------------------------------------
void UART_TxChar(unsigned char ch)
{
    SBUF = ch;

    while(TI == 0);

    TI = 0;
}

//------------------------------------
// UART Transmit Array
//------------------------------------
void UART_TxArray(const __code unsigned char *arr, unsigned int len)
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
unsigned char UART_RxChar(void)
{
    while(RI == 0);

    RI = 0;

    return SBUF;
}

//------------------------------------
// UART Receive Array
//------------------------------------
void UART_RxArray(unsigned char *buf, unsigned int len)
{
    unsigned int i;

    for(i = 0; i < len; i++)
    {
        buf[i] = UART_RxChar();
    }
}

//------------------------------------
// Delay
//------------------------------------
void Delay(unsigned int ms)
{
    unsigned int i,j;

    for(i = 0; i < ms; i++)
    {
        for(j = 0; j < 1275; j++);
    }
}

//------------------------------------
// Send Command And Check ACK
//------------------------------------
__bit SendCommand(const __code unsigned char *cmd,
                unsigned int cmd_len)
{
    UART_TxArray(cmd, cmd_len);

    // ACK packet usually 12 bytes
    UART_RxArray(RxBuf,12);

    /*
        ACK Structure:

        RxBuf[9] = Confirmation Code

        0x00 = Success
    */

    if(RxBuf[9] == 0x00)
    {
        return 1;
    }
    else
    {
        return 0;
    }
}

//------------------------------------
// Wait Until Finger Detected
//------------------------------------
void WaitForFinger(void)
{
    while(1)
    {
        if(SendCommand(GenImg,12))
        {
            break;
        }

        Delay(300);
    }
}

//------------------------------------
// Enroll Fingerprint
//------------------------------------
__bit EnrollFinger(void)
{
    WaitForFinger();

    Delay(1000);

    if(!SendCommand(Img2Tz1,13))
        return 0;

    Delay(3000);

    WaitForFinger();

    Delay(1000);

    if(!SendCommand(Img2Tz2,13))
        return 0;

    Delay(1000);

    if(!SendCommand(RegModel,12))
        return 0;

    Delay(1000);

    if(!SendCommand(Store,15))
        return 0;

    return 1;
}

//------------------------------------
// Main
//------------------------------------
void main(void)
{
    UART_Init();

    Delay(2000);

    EnrollFinger();

    while(1)
    {

    }
}