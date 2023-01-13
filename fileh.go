package main

import (
	"crypto/aes"
	"encoding/hex"
	"fmt"
	"os"
	"strings"
	"sync"
	"time"
)

func main() {

	in := stage1()
	// cipher key
	key := "thisis32bitlongpassphraseimusing"

	out := make(chan string)
	wg := new(sync.WaitGroup)
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go stage2(in, out, wg, []byte(key))

	}

	go func() {
		wg.Wait()
		close(out)
	}()

	//stage3
	fmt.Println("stage 3")
	totalFileBody := ""
	for cnt := range out {
		totalFileBody += ("@@" + cnt)
	}

	fmt.Println("Total hash:", totalFileBody)
	///////////////////un hashing
	unHashwg := new(sync.WaitGroup)
	unHasChan := make(chan string)
	for _, hashline := range strings.Split(totalFileBody, "@@") {
		fmt.Println(hashline)
		if hashline != "" {
			unHashwg.Add(1)
			go DecryptAES([]byte(key), hashline, unHashwg, unHasChan)
		}

	}

	go func() {
		unHashwg.Wait()
		close(unHasChan)
	}()

	for cnt := range unHasChan {
		fmt.Println(cnt)
	}
}
func stage2(in <-chan string, out chan<- string, wp *sync.WaitGroup, hashKey []byte) {
	defer wp.Done()
	//todo: hash line and sendas
	for line := range in {
		out <- EncryptAES(hashKey, line)
	}
}

func stage1() <-chan string {

	ch := make(chan string, 5)

	go func() {
		defer close(ch)

		f := ReadFile()
	loop:
		for _, line := range strings.Split(f, "\n") {
			select {
			case ch <- line:
				continue
			case <-time.After(time.Millisecond * 10):

				break loop
			}
		}

	}()

	return ch
}

func ReadFile() string {

	f, err := os.ReadFile("test.txt")
	if err != nil {
		panic("file Cant Read")
	}
	return string(f)
}

func StageUnHashin(hashPart, wg *sync.WaitGroup, key []byte) {

	defer wg.Done()

}

func EncryptAES(key []byte, plaintext string) string {
	// create cipher
	c, err := aes.NewCipher(key)
	CheckError(err)

	// allocate space for ciphered data
	out := make([]byte, len(plaintext))

	// encrypt
	c.Encrypt(out, []byte(plaintext))
	// return hex string
	return hex.EncodeToString(out)
}

func DecryptAES(key []byte, ct string, wg *sync.WaitGroup, outchan chan<- string) {
	defer wg.Done()

	fmt.Println("input bloack", ct)
	ciphertext, _ := hex.DecodeString(ct)

	c, err := aes.NewCipher(key)
	CheckError(err)

	pt := make([]byte, len(ciphertext))
	c.Decrypt(pt, ciphertext)

	s := string(pt[:])

	outchan <- s
	fmt.Println("DECRYPTED:", s)
}

func CheckError(er error) {
	fmt.Println(er)
}
