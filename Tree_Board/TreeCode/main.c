#ifndef F_CPU
#define F_CPU 1000000UL
#endif

#include <avr/io.h>
#include <avr/interrupt.h>
#include <stdint.h>

// PB0 - LED1 (OC0A)
// PB1 - LED2 (OC0B)
// PB2 - BUTTON (INT0)
#define LED1 (1 << PB0)
#define LED2 (1 << PB1)
#define BUTTON_1 (1 << PB2)


volatile uint8_t mode_selector = 0;
volatile uint8_t mode_changed = 1;
volatile uint16_t millis_counter = 0;
volatile uint8_t debounce_counter = 0;

volatile uint8_t blink_state = 0;
volatile uint16_t blink_timer = 0;

volatile uint8_t pwm_duty = 0;
volatile int8_t pwm_direction = 1;
volatile uint8_t pwm_timer = 0;

void pwm_init(void);
void pwm_disable(void);
void timer1_init(void);
void pwm_setDutyCycle(uint8_t duty_led1, uint8_t duty_led2);

ISR(TIMER1_COMPA_vect)
{
    millis_counter++;
    
    if (debounce_counter > 0) {
        debounce_counter--;
    }

    if (blink_timer > 0) {
        blink_timer--;
    }

    if (pwm_timer > 0) {
        pwm_timer--;
    }
}

ISR(INT0_vect)
{
    if (debounce_counter == 0) {
        mode_selector++;
        if (mode_selector > 2) {
            mode_selector = 0;
        }
        mode_changed = 1;
        debounce_counter = 50;
    }
}

void timer1_init(void)
{

    TCCR1 = (1 << CTC1) | (1 << CS12);
    OCR1C = 125 - 1;
    OCR1A = 125 - 1;
    TIMSK |= (1 << OCIE1A);
}

void pwm_init(void)
{
    TCCR0A = (1 << COM0A1) | (1 << COM0B1) | (1 << WGM01) | (1 << WGM00);
    TCCR0B = (1 << CS01) | (1 << CS00);
    OCR0A = 0;
    OCR0B = 255;
}

void pwm_disable(void)
{
    TCCR0A &= ~((1 << COM0A1) | (1 << COM0B1));
    PORTB &= ~(LED1 | LED2);
}

void pwm_setDutyCycle(uint8_t duty_led1, uint8_t duty_led2)
{
    if (duty_led1 == 0) {
        TCCR0A &= ~(1 << COM0A1);
        PORTB &= ~LED1;
    } else if (duty_led1 == 255) {
        TCCR0A &= ~(1 << COM0A1);
        PORTB |= LED1;
    } else {
        TCCR0A |= (1 << COM0A1);
    }
    OCR0A = duty_led1;

    if (duty_led2 == 0) {
        TCCR0A &= ~(1 << COM0B1);
        PORTB &= ~LED2;
    } else if (duty_led2 == 255) {
        TCCR0A &= ~(1 << COM0B1);
        PORTB |= LED2;
    } else {
        TCCR0A |= (1 << COM0B1);
    }
    OCR0B = duty_led2;
}

void mode_blink_update(void)
{
    if (blink_timer == 0) {
        blink_timer = 500;
        
        if (blink_state == 0) {
            PORTB |= LED1;
            PORTB &= ~LED2;
            blink_state = 1;
        } else {
            PORTB &= ~LED1;
            PORTB |= LED2;
            blink_state = 0;
        }
    }
}

void mode_pwm_update(void)
{
    if (pwm_timer == 0) {
        pwm_timer = 5;
        
        pwm_setDutyCycle(pwm_duty, 255 - pwm_duty);
        
        pwm_duty += pwm_direction;
        
        if (pwm_duty == 255) {
            pwm_direction = -1;
        } else if (pwm_duty == 0) {
            pwm_direction = 1;
        }
    }
}

int main(void)
{
    DDRB |= LED1 | LED2;
    DDRB &= ~BUTTON_1;
    PORTB |= BUTTON_1;
    PORTB &= ~(LED1 | LED2);

    MCUCR &= ~(1 << ISC00);
    MCUCR |= (1 << ISC01);
    GIMSK |= (1 << INT0);
    GIFR |= (1 << INTF0);

    timer1_init();
    
    sei();

    uint8_t current_mode = 0;
    
    while (1) {
        if (mode_changed) {
            mode_changed = 0;
            current_mode = mode_selector;

            pwm_disable();
            blink_state = 0;
            blink_timer = 0;
            pwm_duty = 0;
            pwm_direction = 1;
            pwm_timer = 0;

            if (current_mode == 1) {
                pwm_init();
            }
        }
        
        switch (current_mode) {
            case 0:
                mode_blink_update();
                break;
            
            case 1:
                mode_pwm_update();
                break;
            case 2:
                PORTB |= LED1;
                PORTB |= LED2;
                break;
            
        }
    }
    
    return 0;
}
