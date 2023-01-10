package main

import (
	"fmt"
	"os"
	"strings"
	"sync"
	"time"
)

func main() {

	in := stage1()

	out := make(chan int)
	wg := new(sync.WaitGroup)
	for i := 0; i < 5; i++ {
		wg.Add(1)
		go stage2(in, out, wg)

	}

	go func() {
		wg.Wait()
		close(out)
	}()

	//stage3
	fmt.Println("stage 3")
	count := 0
	for cnt := range out {
		count += cnt
	}

	fmt.Println("word count ", count)

}
func stage2(in <-chan string, out chan<- int, wp *sync.WaitGroup) {
	defer wp.Done()

	for line := range in {
		out <- len(strings.Split(line, " "))
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
