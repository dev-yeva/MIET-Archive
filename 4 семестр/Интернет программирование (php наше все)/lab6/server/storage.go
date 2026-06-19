package main

import (
	"encoding/json"
	"fmt"
	"os"
	"sync"
)

type Storage struct {
	Path   string
	Emails []Email
	mu     sync.Mutex
}

type Email struct {
	ID       string `json:"id"`
	Datatime string `json:"datatime"`
	Subject  string `json:"subject"`
	From     string `json:"from"`
	Message  string `json:"message"`
}

func LoadStorage(path string) *Storage {
	data, err := os.ReadFile(path)
	if err != nil {
		return &Storage{
			Path:   path,
			Emails: []Email{},
		}
	}

	var emails []Email
	if err := json.Unmarshal(data, &emails); err != nil {
		return &Storage{
			Path:   path,
			Emails: []Email{},
		}
	}

	return &Storage{
		Path:   path,
		Emails: emails,
	}
}

func (s *Storage) SaveEmail(email Email) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.Emails = append(s.Emails, email)

	data, err := json.MarshalIndent(s.Emails, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal error: %w", err)
	}

	return os.WriteFile(s.Path, data, 0644)
}
