package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

const baseURL = "http://localhost:8080/emails"

type Email struct {
	ID       string `json:"id"`
	Datatime string `json:"datatime"`
	Subject  string `json:"subject"`
	From     string `json:"from"`
	Message  string `json:"message"`
}

func getEmails() error {
	resp, err := http.Get(baseURL)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}

	fmt.Println("GET /emails response:")
	fmt.Println(string(body))
	return nil
}

func createEmail(email Email) error {
	data, err := json.Marshal(email)
	if err != nil {
		return err
	}

	resp, err := http.Post(baseURL, "application/json", bytes.NewBuffer(data))
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}

	fmt.Println("POST /emails response:")
	fmt.Println(string(body))

	return nil
}

func main() {

	getEmails()

	// POST
	email := Email{
		ID:       "mail999999",
		Datatime: "2026-04-29T12:30:00Z",
		Subject:  "Hello from client",
		From:     "client@mail.com",
		Message:  "Test message",
	}

	createEmail(email)

}
